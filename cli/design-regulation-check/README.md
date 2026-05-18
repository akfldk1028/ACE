# Design Regulation Check CLI

This folder verifies the `/design` legal-geometry path before opening the VWorld/Cesium screen.

It calls:

1. `POST /design/site-boundary/`
2. `POST /design/auto-constraints/`

and checks that parcel geometry, NGII datum, adjacent setback, road/building-line setback, and daylight envelope are present for each case.

For steep `SLOPE_GT3M` cases, the CLI also checks that `datum_result.split_bands` is present. These are 3m elevation-band datum metadata from the DEM boundary profile, not final contour-clipped area polygons.

The CLI now also checks datum/envelope basis:

- `sunlight_envelope.datum_elevation_m` must match `datum_result.neighbor_avg_datum_m` when north sunlight is returned and neighbor average exists.
- `sunlight_envelope.datum_case` must be `neighbor_avg_86` in that case.
- `daylight_diagonal_envelope.walls` must contain valid relative heights.
- Boolean expectations are strict: `expectSunlight: false` fails if sunlight is returned.

## Run

One command for local manual review:

```bash
node cli/design-regulation-check/start-local.mjs
```

This starts:

- Django backend on `http://127.0.0.1:18000`
- Vite `/design` frontend on `http://127.0.0.1:5174/design`
- the full regulation gate below, using the same backend

Use `--no-verify` when you only want to open the page quickly.

Start the local ARR backend first:

```bash
cd ARR/backend
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Then run:

```bash
node cli/design-regulation-check/check-design.mjs
```

Optional:

```bash
node cli/design-regulation-check/check-design.mjs --base http://127.0.0.1:8000 --cases cli/design-regulation-check/cases.json --out cli/design-regulation-check/out/latest.json
```

Expected datum source for local Seoul cases is `ngii_local_dem`. If it falls back to `open_meteo`, do not trust the legal envelope height.

## Run Everything

Use this as the default gate before trusting `/design`:

```bash
node cli/design-regulation-check/run-all.mjs --base http://127.0.0.1:8000
```

It runs:

- API regulation gate
- SVG section render gate
- Python matplotlib section gate
- Python matplotlib plan gate
- Python PNG pixel verification gate
- Python NGII DEM coverage report
- backend datum/setback unit tests

Optional browser capture gate:

```bash
node cli/design-regulation-check/run-all.mjs --base http://127.0.0.1:18000 --frontend http://127.0.0.1:5191 --skip-backend-tests --with-vworld-captures
```

This adds Windows Chrome screenshots of `/design?pnu=<resolved PNU>` for every bundled case.

Output summary:

```text
cli/design-regulation-check/out/run-all-summary.json
```

Use `--skip-backend-tests` if you only need API/visual artifacts.

## Render A Legal Section SVG

When the VWorld/Cesium frontend is suspect or Playwright cannot drive the page, render a deterministic 2D section from the same `/design` API response:

```bash
node cli/design-regulation-check/render-section.mjs --base http://127.0.0.1:8000
```

Output:

```text
cli/design-regulation-check/out/sections/*.svg
cli/design-regulation-check/out/sections/summary.json
```

The SVG shows:

- `대지 §119 H0`
- `전면도로 기준`
- `인접대지 기준`
- `§86 평균수평면`
- north sunlight envelope when returned
- daylight diagonal envelope when returned

Pass criteria:

- `sunlight_envelope.datum_elevation_m` equals `datum_result.neighbor_avg_datum_m` when the neighbor average exists.
- `daylight_diagonal_envelope` is drawn from `datum_result.parcel_datum_m`.
- `datum_result.elevation_source` remains `ngii_local_dem`.
- `expectSunlight: false` and `expectDaylight: false` cases fail if the envelope is unexpectedly returned.

## Render With Python / Matplotlib

Python version, useful when you want PNG plots and a normal Python test harness:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/render_section.py --base http://127.0.0.1:8000
```

Output:

```text
cli/design-regulation-check/out/pysections/*.png
cli/design-regulation-check/out/pysections/summary.json
```

It uses `matplotlib` from `ARR/backend/.venv`, calls `/design/site-boundary/` and `/design/auto-constraints/`, applies the same datum/envelope assertions, and exits non-zero on failure.

## Render A Legal Plan PNG

Plan-view datum QA, used to verify that `대지레벨`, `도로레벨`, `인접대지레벨`, and `§86 평균수평면` are attached to the correct parcel/road/neighbor geometry before trusting VWorld:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/render_plan.py --base http://127.0.0.1:8000
```

Output:

```text
cli/design-regulation-check/out/plan/*.png
cli/design-regulation-check/out/plan/summary.json
```

The PNG draws:

- parcel boundary and parcel §119 weighted-average sample points,
- road frontages and road centerline elevation samples,
- neighbor parcels/shared edges and neighbor datum labels,
- buildable area and returned legal offset lines.

Pass criteria include `ngii_local_dem`, parcel/road/neighbor datum presence, and basic geometry sanity: road/neighbor shared edges must be near the site boundary.

Plan PNGs use a dedicated verifier. Do not run the section pixel verifier
against plan PNGs because it expects section-only colors such as daylight
purple and §86 horizontal lines.

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/verify_plan_images.py --summary cli/design-regulation-check/out/plan/summary.json
```

It checks that the PNG exists, is nonblank, uses `ngii_local_dem`, and has
numeric parcel/road/neighbor/§86 datum values plus enough parcel/road/neighbor
samples to make the displayed labels trustworthy.

## Verify Generated PNG Pixels

`run-all.mjs` automatically runs this after Python rendering:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/verify_images.py
```

It reopens the generated PNG files with Pillow and checks:

- image dimensions,
- non-background pixel ratio,
- parcel/road/neighbor/§86 datum line colors,
- sunlight/daylight envelope colors,
- test mass color.

Output:

```text
cli/design-regulation-check/out/pysections/image-check.json
```

## Check NGII DEM Coverage

The legal datum gate only trusts parcels covered by the configured local NGII GeoTIFF. To report covered and missing parcels:

```bash
ARR/backend/.venv/bin/python cli/design-regulation-check/check_dem_coverage.py --base http://127.0.0.1:8000
```

Output:

```text
cli/design-regulation-check/out/dem-coverage.json
```

Current bundled coverage expectations:

- `강남구 도곡동 467-3`: covered
- `강남구 대치동 1028`: covered
- `강남구 역삼동 677`: not covered by the current `seoul_dem.tif`; add another NGII tile before using it as a legal datum regression case

## Capture VWorld / Cesium Screenshots

Use this when the user needs to inspect the actual `/design` overlay, not only deterministic PNG/SVG plots:

```bash
node cli/design-regulation-check/capture-vworld.mjs --base http://127.0.0.1:18000 --frontend http://127.0.0.1:5191
```

Output:

```text
cli/design-regulation-check/out/vworld/*.png
cli/design-regulation-check/out/vworld/summary.json
```

The script resolves each case through `/design/site-boundary/`, opens `/design?pnu=<PNU>` in Windows Chrome headless, and writes a PNG. Use `--query layers=all` for full debug overlays or `--query roadLabels=all` for every road label.
