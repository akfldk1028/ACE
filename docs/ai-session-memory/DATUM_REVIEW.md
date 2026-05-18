# Datum Review

Date: 2026-05-18

## Current Verdict

For the two bundled Gangnam legal-review cases, datum is currently verified enough to use in `/design`:

- `강남구 도곡동 467-3` / `1168011800104670003`
- `강남구 대치동 1028` / `1168010600110280000`

Both pass:

- API datum gate,
- plan-view datum geometry gate,
- plan PNG nonblank/numeric/sample-count gate,
- `elevation_source == ngii_local_dem`.

Do not generalize this to every Seoul parcel until NGII DEM coverage is confirmed for that parcel.

## Datum Pipeline

Entry path:

1. `/design/auto-constraints/`
2. `ARR/backend/design/views.py`
3. `land.services.setback_geometry.compute_setback_lines(...)`
4. `_maybe_compute_datum(...)`
5. `land.services.datum.cases.compute_datum_elevation(...)`
6. `land.services.datum.calculator`
7. `land.services.datum.elevation_api`

Core calculations:

- `parcel_datum_119(parcel_wgs)`: samples parcel boundary segments, splits long edges, and returns the horizontal-length weighted average datum.
- `road_datum_119(road_centerline_wgs)`: samples road centerline and returns weighted road datum metadata.
- `neighbor_datum_m`: computed by applying the same parcel datum function to the selected north-side neighbor parcel.
- `neighbor_avg_datum_86`: `(parcel_datum_m + neighbor_datum_m) / 2`.
- `sunlight_envelope.datum_elevation_m`: should use the §86 neighbor average when available.
- building mass and daylight envelope should use `parcel_datum_m`, not the §86 average.

Strict data-source rule:

- Legal datum is trustworthy only when `datum_result.elevation_source == "ngii_local_dem"`.
- `ngii_local_dem` refuses silent Open-Meteo fallback when samples are outside the configured local DEM.

## Verified Output

Generated artifacts:

- `cli/design-regulation-check/out/plan-datum-review/Gangnam_Dogok_467-3.png`
- `cli/design-regulation-check/out/plan-datum-review/Gangnam_Daechi_1028.png`
- `cli/design-regulation-check/out/plan-datum-review/summary.json`
- `cli/design-regulation-check/out/plan-datum-review/image-check.json`

Observed values:

| Case | Parcel Datum | Road Datum | Neighbor Datum | §86 Average | Samples |
| --- | ---: | ---: | ---: | ---: | --- |
| Dogok 467-3 | 15.00m | 15.00m | 15.00m | 15.00m | parcel 36 / road 10 / neighbor 196 |
| Daechi 1028 | 15.00m | 15.00m | 16.37m | 15.68m | parcel 112 / road 4 / neighbor 47 |

These plan PNGs place the labels on parcel/road/neighbor geometry, not on an arbitrary grid.

## Verification Commands

API gate:

```bash
node cli/design-regulation-check/check-design.mjs --base http://127.0.0.1:18000 --out cli/design-regulation-check/out/latest-datum-review.json
```

Plan render gate:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/render_plan.py --base http://127.0.0.1:18000 --out-dir cli/design-regulation-check/out/plan-datum-review --timeout 240
```

Plan image gate:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/verify_plan_images.py --summary cli/design-regulation-check/out/plan-datum-review/summary.json --out cli/design-regulation-check/out/plan-datum-review/image-check.json
```

`run-all.mjs` now runs `verify_plan_images.py` after `render_plan.py`. Do not use `verify_images.py` for plan PNGs; it is section-specific and expects section-only colors.

## Known Gaps

- Article 119 `>3m` segmentation still returns DEM boundary-profile `split_bands`; it is not yet true contour-clipped area polygon segmentation.
- DEM coverage must be checked for new parcels before trusting legal height envelopes.
- Road datum is metadata unless the relevant legal case requires road datum application; current `/design` primarily uses parcel datum for mass/daylight and §86 average for north sunlight.
- Neighbor datum depends on correct north-side neighbor selection from `neighbor_parcels`.

## Next AI Rule

Before saying “대지레벨 정확함,” verify:

1. `datum_result` exists.
2. `elevation_source == ngii_local_dem`.
3. `parcel_datum_m`, `road_datum_m`, `neighbor_datum_m`, `neighbor_avg_datum_m` are numeric when the legal layer needs them.
4. Plan PNG labels are attached to parcel/road/neighbor geometry.
5. If `case == slope_gt3m`, do not claim full §119 compliance until true area polygon segmentation exists.
