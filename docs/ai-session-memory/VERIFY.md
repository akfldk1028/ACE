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
