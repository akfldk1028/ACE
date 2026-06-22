# Implementation Decisions

## Decision 1: Do Not Trust Single-Image Beauty Renders

Single-image facade output is useful for mood and visual communication, but it
does not prove that the model understood the 3D MAAS geometry.

Decision:

- Single-image output may be shown as a preview.
- Legal geometry remains `mass_geojson`.
- Provider output cannot change legal status.

## Decision 2: Multi-View Pack Is the Minimum Viable Condition

Before depth/normal/projection exists, a deterministic multi-view sheet is the
lowest useful step.

Implemented:

- `front`
- `right`
- `back`
- `left`
- `axon`
- `top`

Decision:

- The aesthetic endpoint defaults to `MultiViewReferencePackRenderer`.
- Legacy `ReferencePngRenderer` remains for tests and fallback only.

## Decision 3: Scene Graph Is Required

The image model needs structural language beyond pixels.

Current graph:

```text
site
legal_envelope
mass
volume_*
facade_front/right/back/left
```

Next graph fields:

- facade plane normal.
- floor range per facade.
- road-facing facade.
- sunlight-constrained facade.
- terrace/setback relation.
- material zones.

## Decision 4: VWorld Overlay Is Only a Preview, Not Aesthetic Mode

The VWorld billboard overlay was useful for early inspection, but it confused
the main requirement: the facade must be applied to the existing MAAS mass, not
float above it as an image card.

Decision:

- Keep provider images in the right-side panel for inspection.
- Do not render the provider image as a billboard when a facade texture/material
  is already applied to the mass.
- Do not describe it as facade projection.
- Add real projection only after facade planes and texture coordinates exist.

## Decision 5: Apply Facade Style To Existing MAAS Mass First

The user requirement is not just "show an image beside the mass." The selected
MAAS `mass_geojson` is the source of truth, and facade styling must be applied
back onto that existing 3D mass.

Implemented first step:

- Frontend mass rendering moved from `SiteMapPanel` into
  `ARR/frontend/src/design/lib/cesium/mass-entities.ts`.
- Prompt-to-material wall rendering lives in
  `ARR/frontend/src/design/lib/cesium/facade-materials.ts`.
- Shape labels/colors live in
  `ARR/frontend/src/design/lib/cesium/mass-styles.ts`.
- `InteractiveDesignPanel` sends the rendered `massGeojson.properties.design_id`
  to the aesthetic endpoint before falling back to UI `design.id`.
- Cesium wall entities with ids like `design-mass-facade-*` are generated on the
  existing mass floor groups/volumes/plates.
- Brick/glass/concrete/etc. prompts map to procedural facade material palettes;
  brick now uses a canvas texture pattern instead of only a flat color.

Verified:

- `npm run type-check` passes.
- Windows Chrome CDP Playwright loop against
  `http://127.0.0.1:5174/design` passed after frontend/backend restart.
- Latest loop produced `facadeAttempts: 4`, `facadeEligibleFeatures: 1`,
  `overlayAttempts: 1`, and 27 `design-mass-facade-*` entities for design
  `900000`.
- Screenshot:
  `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_check.png`.

Still not done:

- Procedural brick now has joint/window rhythm and is useful for verifying that
  style is applied to the existing mass, but it is not true photoreal output.
- Realistic facade quality must come from GPT Image / Nano Banana generated
  assets, not hand-coded procedural texture.
- Frontend now has a `aestheticFacadeTextureUrl` path: when provider assets
  include a generated image URL, that URL is used as the Cesium wall material
  image on the existing mass.
- Next step is per-facade texture projection from generated assets using the
  sidecar `facade_planes.json` and stable wall plane IDs, instead of applying
  the same generated image to all facade walls.

## Decision 6: Provider Images Must Be Projected Onto Existing Mass, Not Shown Only Beside It

Implemented and verified on 2026-06-10:

- GPT Image and Nano Banana outputs are used as `aestheticFacadeTextureUrl`.
- Frontend crops the generated multi-view atlas into front/right/back/left
  panels and assigns panels to Cesium facade wall entities by edge direction.
- Texture mode removes the opaque extruded mass side surfaces so image walls
  are not hidden by the legal orange mass.
- Texture mode suppresses mass/facade helper outlines on the facade surface.
- `DesignPage` now passes the active rendered `massGeojson` to
  `InteractiveDesignPanel`; if a UI row id and rendered MAAS mass id diverge
  during streaming, the aesthetic endpoint uses the actual visible mass id.
- Playwright now waits for optimization `COMPLETE` before triggering provider
  generation.

Provider verification:

- GPT Image: `gpt-image · pass / complete`.
  - Generated asset:
    `ARR/backend/media/maas/aesthetic/generated/maas_evidence_9da76070_78ac_437e_ac28_6f87679509d9_900000_maas_01.openai.png`
  - Screenshot:
    `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_closeup_gpt-image.png`
- Nano Banana: `nano-banana · pass / complete`.
  - Initial configured model `gemini-2.5-flash-image-preview` returned 404.
  - Adapter now falls back to `nano-banana-pro-preview`, then
    `gemini-2.5-flash-image`, then newer image models.
  - Generated asset:
    `ARR/backend/media/maas/aesthetic/generated/maas_evidence_e59304d0_3341_4497_892b_3f07c5826147_900000_maas_01.nano-banana.png`
  - Screenshot:
    `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_closeup_nano-banana.png`

Remaining visual limitation:

- The facade is now on the existing VWorld MAAS mass, and aesthetic preview mode
  hides legal envelope/reference layers while the facade texture is active.
- The previous direct image projection produced ugly repeated/collaged texture.
  Current implementation intentionally uses a structured facade canvas on the
  Cesium wall planes instead of pasting one provider render as wallpaper.
- This is cleaner and readable as a building, but it is still procedural
  viewport material, not true paper-quality photoreal 3D texture synthesis.

## Decision 7: Procedural Facade Grammar Is The Current Safe VWorld Bridge

Implemented on 2026-06-10 after visual review of the bad repeated-brick
screenshots:

- `texture-shell` mode attaches facade entities once around the selected mass
  instead of once per floor group/volume/layer.
- Legal envelope/setback/datum diagnostics are cleared in aesthetic preview mode.
- Provider image billboard is suppressed when `aestheticFacadeTextureUrl` exists.
- `facadePaletteFromStyle` prioritizes `brick` over `limestone`, so prompts like
  “warm brick and limestone base” render as warm brick massing instead of gray
  stone.
- `createDesignedFacadeCanvas()` draws base/middle/top, deep window reveals,
  balconies, ground-floor entrance, and restrained material grain.

Verified:

- `npm run type-check` passes.
- GPT Image Playwright loop passed:
  `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_closeup_gpt-image.png`.
- Fast reference texture probe passed after Vite restart:
  `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_closeup_placeholder.png`.
- Latest debug state:
  `facadeAttempts: 1`, `overlayAttempts: 0`, facade entities only
  `design-mass-facade-900000-texture-shell-*`.

Assessment:

- The grotesque repeated texture problem is fixed.
- The mass now reads as one coherent warm-brick building in VWorld.
- It is not yet photoreal like a final GPT/Nano Banana render; the next real
  quality jump needs per-facade generated images with UV/projection consistency,
  not more hand-coded canvas details.

## Decision 8: Provider Output Is Split Into Facade Panel Assets

Implemented on 2026-06-10:

- Added `design.maas.aesthetic.projection_assets.attach_facade_panel_assets`.
- Provider `generated_facade_image` outputs are cropped into deterministic panel
  assets:
  - `front.panel.png`
  - `right.panel.png`
  - `back.panel.png`
  - `left.panel.png`
  - `axon.panel.png`
  - `top.panel.png`
- `provider_result.metadata.facade_projection` records:
  - projection mode,
  - source asset id,
  - panel asset ids,
  - reference condition pack id.
- Frontend `MaasAestheticResult` accepts asset metadata with `view`.
- `DesignPage` builds `texturePanelUrls` from `facade_panel_image` assets.
- `SiteMapPanel -> renderMassEntities -> renderFacadeWallEntities` now passes
  the panel URL map to Cesium facade material generation.
- `facade-materials.ts` uses the per-view provider panel as a low-strength
  material seed under the structured facade grammar, avoiding direct wallpaper
  projection.

Verified:

- Backend direct API call returned `generated_facade_image` plus 6
  `facade_panel_image` assets.
- Backend served `front/right/back/left.panel.png` with HTTP 200.
- Frontend Playwright GPT Image loop passed.
- Latest `window.__arrLastMassRender` showed:
  - `facadeTexturePanelViews: ["front", "right", "back", "left", "axon", "top"]`
  - `facadeAttempts: 1`
  - `overlayAttempts: 0`
- Latest screenshots:
  - `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_check_gpt-image.png`
  - `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_closeup_gpt-image.png`

Assessment:

- This is now structurally aligned with the paper direction: view-conditioned
  facade panels are addressable by facade direction.
- It is still not full UV baking or neural multi-view texture optimization.
- The next step is to replace low-strength panel seeding with a real projection
  worker that bakes per-plane textures onto exported mesh/UVs.

## Decision 9: Projection Worker Starts As A Manifest Contract

Implemented on 2026-06-10:

- Added `design.maas.aesthetic.projection_mesh`.
- `build_projection_manifest(volumes, bounds)` derives facade surfaces from the
  locked MAAS volume rings.
- Each surface has:
  - stable `id`,
  - `volume_id`,
  - `view` / `plane_id`,
  - 4 local-meter vertices,
  - 4 normalized atlas UVs,
  - 2 triangles,
  - area/edge/height metrics,
  - source panel role/view.
- `MultiViewReferencePackRenderer` now writes
  `projection_manifest.json` into the condition pack.
- `/design/jobs/.../aesthetic/` exposes the manifest URL under
  `reference.metadata.condition_pack.projection_manifest.url`.

Verified:

- `manage.py test design.test_maas_export.MaasAestheticImageJobTest` passed.
- `npm run type-check` passed.
- Direct placeholder API call returned `projection_manifest.url`.
- Direct manifest inspection produced 9 facade surfaces with
  `front/right/back/left` views for the test MAAS mass.

Assessment:

- This is a maintainable first step toward real UV baking: the texture worker
  can now consume a stable manifest instead of reverse-engineering Cesium walls.
- It still does not create a baked texture image or glTF mesh; that remains the
  next implementation step.

## Decision 10: Deterministic Texture Bake Is Now A Pipeline Asset

Implemented on 2026-06-10:

- Added `design.maas.aesthetic.projection_bake`.
- `attach_baked_projection_assets()` consumes:
  - `projection_manifest.json`,
  - local `facade_panel_image` assets,
  - provider metadata.
- It writes:
  - `baked_texture_atlas.png`,
  - `bake_manifest.json`.
- The bake manifest records:
  - source projection manifest,
  - source panel asset ids,
  - texture atlas URI,
  - surface UVs/triangles/source panel views,
  - `legal_status_effect: none`.
- `pipeline.py` now runs:
  - provider generation,
  - facade panel crop,
  - deterministic texture bake,
  - provider validation.

Verified:

- Added unit coverage for crop + bake using a fake generated multi-view image.
- `manage.py test design.test_maas_export.MaasAestheticImageJobTest` passed with
  7 tests.
- `npm run type-check` passed.
- Direct GPT Image API call returned assets with roles:
  - `generated_facade_image`,
  - six `facade_panel_image` assets,
  - `baked_texture_atlas`,
  - `texture_bake_manifest`.
- Direct visual inspection of
  `ARR/backend/media/maas/aesthetic/generated/.../baked_texture_atlas.png`
  showed a coherent 3x2 atlas with front/right/back/left/axon/top facade panels.

Assessment:

- The pipeline now has an actual texture atlas artifact, not only a VWorld
  preview material.
- It is still a deterministic panel-atlas bake, not yet a glTF/mesh export or
  neural multi-view optimization pass.

## Decision 11: Baked Atlas Exports As Textured Mesh/glTF

Implemented on 2026-06-10:

- Added `design.maas.aesthetic.projection_export`.
- `attach_textured_mesh_assets()` consumes:
  - `texture_bake_manifest`,
  - `baked_texture_atlas`,
  - the source `projection_manifest.json`.
- It writes:
  - `textured_mesh_manifest.json`,
  - `textured_mesh.gltf`.
- The mesh manifest contains local-meter positions, UVs, triangle indices, and
  per-surface index ranges.
- The glTF embeds the mesh buffer and references `baked_texture_atlas.png` as a
  relative image URI.
- `pipeline.py` now runs:
  - provider generation,
  - facade panel crop,
  - deterministic texture bake,
  - textured mesh/glTF export,
  - provider validation.
- Frontend `DesignPage -> SiteMapPanel -> renderMassEntities` now passes
  `textured_gltf` URLs.
- Cesium loads the glTF with an east/north/up transform from the first MAAS ring
  point, matching the backend projection coordinate space.
- The asset dev server now serves `.gltf` as `model/gltf+json`.

Verified:

- Unit coverage validates `textured_mesh_manifest` and `textured_gltf` assets.
- `manage.py test design.test_maas_export.MaasAestheticImageJobTest` passed.
- `npm run type-check` passed.

Assessment:

- The pipeline now has a reusable 3D texturing artifact, not only a VWorld
  procedural preview.
- The visual quality still depends on provider panel quality and UV consistency.
- Next work is browser visual verification of the loaded glTF and then moving
  beyond deterministic panel baking toward multi-view texture refinement.

## Decision 12: Headed VWorld Verification Is Required For glTF QA

Implemented and verified on 2026-06-10:

- Headless Playwright still falls back to `2D MASS PREVIEW`; it is not valid for
  VWorld/glTF visual QA.
- A separate Windows Chrome profile was launched with CDP and verified in headed
  mode.
- Placeholder headed loop confirmed real VWorld mode:
  - `window.__arrLastMassRender` exists,
  - facade entities render,
  - no 2D fallback.
- GPT Image headed loop confirmed glTF mode:
  - `hasTexturedGltfUrl: true`,
  - `gltfAttempts: 1`,
  - `gltfStatus: added`,
  - `aestheticGltfPrimitives: [{ designId: 900000, ready: true }]`,
  - overlay billboard suppressed,
  - procedural facade wall entities suppressed.
- Projection manifest now also exports `top` roof surfaces, and glTF mode hides
  the old semi-transparent MAAS cap polygons so the aesthetic preview reads more
  like one exterior shell.

Latest screenshots:

- `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_check_gpt-image.png`
- `docs/playwright/design-route-live-verify/windows_chrome_aesthetic_closeup_gpt-image.png`

Assessment:

- The core requirement is now satisfied: provider-generated facade texture is
  converted into a mesh/glTF asset and loaded on the existing MAAS mass inside
  VWorld.
- The result is still first-pass projection quality, not final neural
  multi-view texture optimization.
