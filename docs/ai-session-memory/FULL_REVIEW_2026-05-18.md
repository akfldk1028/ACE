# Full Review - 2026-05-18

This is the current blunt review state for the ARR `/design` legal-visualization work.

## Verdict

Not complete enough to call "perfect legal review."

The datum pipeline is now testable and passes the bundled DEM-covered Gangnam PNU cases, but the product is still a strong prototype, not a Flexity-grade or legally exhaustive checker.

## Connected Projects

- `ARR/`: source of truth for `/design`. Django backend computes cadastral boundary, zoning/regulations, datum, road/neighbor context, and setback/envelope geometries. React/VWorld frontend renders the result.
- `AG-light/`: lightweight Cloudflare/API legal-agent project. It is not yet equivalent to ARR for datum, setback geometry, VWorld visualization, or full regulation coverage.
- `gateway/` / Hermes: agent/tool path. Current tool flow targets land analysis, not the ARR `/design` visual stack. Do not debug `/design` by starting here unless the user asks about agent/chat routing.

## Verified On 2026-05-18

Backend tests:

```text
.venv/bin/python manage.py test land.tests.SetbackGeometryDatumTest land.tests.DatumCasesTest
Ran 15 tests in 48.128s
OK
```

PNU API gate:

```text
node cli/design-regulation-check/check-design.mjs --base http://127.0.0.1:18000 --out cli/design-regulation-check/out/latest-full-review.json
PASS Gangnam Dogok 467-3, PNU 1168011800104670003
PASS Gangnam Daechi 1028, PNU 1168010600110280000
```

Observed values:

- Dogok 467-3: parcel datum `15m/ngii_local_dem`, road datum `15m`, neighbor datum `15m`, sunlight/daylight returned.
- Daechi 1028: parcel datum `15m/ngii_local_dem`, road datum `15m`, neighbor datum `16.36526621971818m`, §86 average `15.68263310985909m`, sunlight/daylight returned.

Plan PNG gate:

- `cli/design-regulation-check/out/plan-datum-review/Gangnam_Dogok_467-3.png`
- `cli/design-regulation-check/out/plan-datum-review/Gangnam_Daechi_1028.png`
- `cli/design-regulation-check/out/plan-datum-review/image-check.json`

The plan image verifier passed for dimensions/nonblank output. These PNGs are the reference for how VWorld should show sparse legal datum markers instead of an elevation grid.

Representative 9-PNU legal/line batch:

```text
.venv/bin/python tools/verify_all.py --backend http://127.0.0.1:18000 --timeout 300 --out ../../cli/design-regulation-check/out/pnu-9-review.json
Result: PASS, 9/9 representative parcels
```

This batch checks zone inclusion, BCR/FAR, sunlight applicability, and registry-driven regulation-line presence. It does not replace datum PNG / section PNG / VWorld capture review.

Important PNU-specific finding:

- `1129010100103300000` / 서울 성북구 성북동 330 returns multiple zones: `자연녹지지역`, `제1종전용주거지역`. The fixture expected zone is still valid because it is included, but any review that reads only `zones[0]` will misread the case.

## Legal Coverage Matrix

| Area | Current State | Review Judgment |
| --- | --- | --- |
| §119 parcel datum | NGII DEM local path is used for covered Seoul cases. Weighted boundary sampling exists. | Usable for verified covered cases only. |
| §119 >3m split | `split_bands` metadata exists for steep profiles. | Not complete. Official law requires the ground plane to be determined for each portion within 3m height difference; true contour/area polygon partition is still missing. |
| Road datum | Road centerline/sample datum is returned as metadata. | Good enough for display and debugging. It is not always applied as the final `datum_result.elevation_m` unless the road datum path is explicitly selected. |
| §86 north sunlight | Uses neighbor average datum for the sunlight envelope when neighbor datum exists. Default VWorld should show compact vertical plus diagonal profile. | Core basis is now testable, but exceptions and all ordinance variants are not exhausted. |
| Daylight diagonal | Backend returns a site-boundary reference surface for 공동주택 with multiplier 2 or 4. | Not a final legal pass/fail. True §86(3) needs actual mass wall/window direction and perpendicular distance/facing-building logic. |
| Front-road diagonal / height | `front_road_diagonal_profile` exists as a reference ribbon/profile. | Not a complete current-law envelope. Road width, opposite boundary, road level, piloti relaxation, and 가로구역별 height rules are not fully modeled. |
| Building line / district plan | Some road/building-line visual context exists. | Weak. Actual district-unit plan line geometry is not reliably extracted. |
| Multi-zone parcels | Strictest-rule logic exists. | Not enough. True area-ratio/zone-split application is still missing. |
| AG-light parity | AG-light exists and is connected conceptually. | Not ARR-equivalent. Do not claim AG-light performs this full review. |

Official-law sanity checks used during review:

- Building Act Enforcement Decree Article 86 is the source for north sunlight/daylight height limits.
- Building Act Enforcement Decree Article 119(2) says when ground height differs, weighted average is used, and if the height difference exceeds 3m, the ground plane is determined for each portion within a 3m difference.
- Building Act Enforcement Decree Article 82 concerns designation/announcement of heights by street block, so old front-road diagonal diagrams should be treated carefully as historical/reference unless a current applicable rule is present.

## VWorld / Flexity Gap

What is working:

- `/design?pnu=<PNU>` browser entry can load the design path.
- Default VWorld has been cleaned compared with the earlier dense debug fences.
- Datum markers can show parcel, road, north-neighbor, and §86 average levels.
- North sunlight profile should remain visible even without mass.
- Daylight is rendered as a sloped polygon instead of a folded Cesium wall.

Still not Flexity-grade:

- There is no polished layer controller and legend that separates legal basis, debug geometry, and user-facing geometry.
- Sunlight/daylight are not clipped/interpreted against a generated mass in a professional review workflow.
- Purple/green legal surfaces can still read as abstract planes unless camera, opacity, labels, and line hierarchy are tuned per layer.
- Road frontage and neighbor context are shown, but the UI does not yet explain enough of the calculation without debug logs/panel.

## Route / Local Server Note

`http://127.0.0.1:18000/` returning Django 404 is normal because URL patterns are `admin/`, `law/`, `land/`, and `design/`.

Use the frontend route for user review:

```text
http://127.0.0.1:<vite-port>/design?pnu=1168010600110280000
```

If `curl http://127.0.0.1:<vite-port>/design...` returns 404 but a browser works, check the request `Accept` header. Vite serves the React app for browser HTML requests; non-browser `Accept: */*` can hit the proxy and return Django 404.

## Dirty Worktree

The repository still has a large pre-existing dirty/untracked state across `AG/`, `ARR/`, `JSON_MODULES/`, `docs/`, and `tests/`. Do not run broad cleanup or broad staging.

Safe policy:

1. Only stage paths changed for the current legal-review task.
2. Keep ARR legal/source changes separate from AG research and JSON agent config.
3. Do not normalize EOL across the tree in the same commit as legal code.
4. Never delete user reference images from `docs/`.

## Next Implementation Order

1. Finish §119 >3m true polygon/area partitioning from DEM/contours.
2. Promote the 9 representative PNU set into the full visual gate: API, plan PNG, section PNG, and VWorld capture per PNU.
3. Add mass-aware daylight verification: wall/window candidates, perpendicular distance rays, same-site facing-building cases, and pass/fail section PNG.
4. Implement current-law front-road / 가로구역 height envelope only after road datum and road width/opposite-boundary extraction are trusted.
5. Convert VWorld into a clean review product: layer toggles, compact legend, stable labels, sparse defaults, debug layers opt-in.
6. Expand PNU regression cases with known slope/road/neighbor scenarios after adding more NGII DEM tiles.
