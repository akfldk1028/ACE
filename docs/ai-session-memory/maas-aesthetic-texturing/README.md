# MAAS Aesthetic Texturing Memory

Purpose: keep the MAAS facade/texturing direction separate from general session
notes. This folder tracks research, cloned code, and implementation decisions
for turning legal MAAS geometry into consistent architectural facade imagery and
eventually projected texture assets.

## Current Direction

The correct path is not:

```text
MAAS mass -> one pretty image -> pretend it is the building
```

The correct path is:

```text
MAAS 3D mass
-> multi-view reference pack
-> scene graph + depth/normal/silhouette/floor guides
-> facade/material image synthesis
-> projection or texture asset back onto the same MAAS mass
-> VWorld/Cesium visual verification
```

## Current Implementation State

- `MultiViewReferencePackRenderer` exists in
  `ARR/backend/design/maas/aesthetic/renderers/multi_view_pack.py`.
- The live aesthetic endpoint now returns a 1536x1536
  `*.multi-view.png` reference sheet.
- Sheet views: `front`, `right`, `back`, `left`, `axon`, `top`.
- Metadata includes `arr.maas.scene_graph.v0`.
- Metadata includes `arr.maas.condition_pack.v0` with sidecar files:
  `scene_graph.json`, `camera_poses.json`, `facade_planes.json`,
  `silhouette/*.png`, `depth/*.png`, and `floor_guides/*.png`.
- GPT Image / Nano Banana prompts are now multi-view consistency prompts.
- VWorld currently shows the generated/reference image as a billboard overlay
  above the selected MAAS mass.
- Playwright loop verification caught and fixed an elevation scaling bug:
  `front/right/back/left` panels were initially rendered as tiny marks at the
  bottom because elevation scale was computed against a 1px height. The renderer
  now uses independent x/z panel scales.

## Not Yet Done

- Physically accurate depth maps.
- Normal maps.
- Pixel-accurate silhouette masks per view.
- Rich facade plane extraction with exact edge-to-view mapping.
- UV/projection mapping.
- Pixel/geometry consistency validation.
- Provider output projected onto Cesium mass surfaces.

## Latest Playwright Loop Evidence

- Loop 1 found: endpoint/UI passed, but the visual reference pack was weak;
  elevation panels were nearly blank and the VWorld overlay looked like a large
  white board.
- Fix: corrected elevation panel x/z scaling in
  `ARR/backend/design/maas/aesthetic/renderers/multi_view_pack.py`.
- Loop 2 passed visually and structurally:
  - right panel shows readable front/right/back/left elevation panels.
  - VWorld overlay entity exists: `design-mass-aesthetic-overlay-900000`.
  - screenshot:
    `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_loop02.png`
  - JSON:
    `docs/playwright/design-route-live-verify/windows-chrome-aesthetic-loop02.json`

## Read Order

1. `PAPERS.md`
2. `CODE_REPOS.md`
3. `IMPLEMENTATION_DECISIONS.md`
4. `NEXT_STEPS.md`
