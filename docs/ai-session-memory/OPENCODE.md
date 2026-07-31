# OpenCode Collaboration Notes

OpenCode was used in tmux pane `0:0.2`.

It was asked to audit `/design`, not `/land`, for:

- backend design endpoints,
- frontend VWorld/Cesium rendering,
- `setback_geometries`,
- datum from NGII DEM,
- road frontage/building line,
- adjacent setback,
- north sunlight/daylight envelopes.

Useful OpenCode findings reflected in this session:

- `/design` uses ARR backend directly.
- `SiteMapPanel.tsx` had daylight diagonal rendering disabled.
- NGII DEM fallback risk is high; `open_meteo` is not acceptable for precise legal envelopes.
- Raw SHP files are not runtime inputs; converted DEM GeoTIFF is the runtime source.
- `buildable_area` is not a full legal intersection of every constraint.

OpenCode did not edit files. Codex made the patches after reviewing its findings.
