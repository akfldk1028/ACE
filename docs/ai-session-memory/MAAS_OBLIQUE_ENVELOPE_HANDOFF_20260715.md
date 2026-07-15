# MAAS oblique-envelope handoff — 2026-07-15

## User intent (do not misread)

The three reference images below are examples of a missing capability, not a
request to turn all 20 candidates into polygon sculptures:

- `docs/KakaoTalk_20260715_095428011.jpg`: wedge/leaning monolith and sloped envelope
- `docs/KakaoTalk_20260715_095428011_01.jpg`: monolith with a diagonal ground undercut
- `docs/KakaoTalk_20260715_095428011_02.jpg`: shifted polygon plate / large sectional opening language

The final portfolio must retain clean stepped, courtyard, ribbon, bridge,
cluster and calm languages. Oblique envelopes are a bounded additional family
(final minimum 1, maximum 2), not a replacement morphology.

## Representation-level correction

Added `source_geometry/oblique_fields.py`. The graph author supplies one
normalized plan polygon and transformations for bottom, shoulder and top
rings. The compiler projects these through the parcel's minimum-rotated frame
and builds one continuous polygon-ring loft. There are no named-building
outlines or parcel-coordinate presets in the production representation.

Important separation:

- One conservative `primary_agent_oblique_envelope_proxy` remains the law/FAR
  solid.
- `agent_oblique_envelope_mesh` is the review/VLM surface representation.
- A valid field compiles to one volume and 9-24 surfaces for 3-8 plan points.
- Invalid/missing plan controls do not silently qualify as oblique geometry.

The production graph author uses primary `taper` plus
`formal_principle=undercut_tapered_tower`, with:

- 3-8 `plan_control_points` forming a real non-self-crossing plan polygon;
- matching scalar `top_height_controls`;
- shoulder fraction and bottom/top scale/shift values.

## Root cause found in first real loop

v95 showed why prompt text alone was insufficient. GPT authored three apparent
oblique candidates, but two used section-like nearly collinear plan points and
one used `[u,height]` pairs inside `top_height_controls`. The old validator only
checked list lengths. The formal compiler then could not build a polygon field
and silently returned the legacy taper geometry.

The author boundary now validates numeric point shape, polygon validity,
minimum normalized area (`>= 0.06`), matching scalar roof heights and required
`x_ratio/y_ratio`. Invalid candidates are rejected before the geometry pool,
and missing executable `oblique_envelope` coverage triggers an author repair
batch.

## Closed-loop behavior

- Bounded program search mutates plan polygon vertices and roof-height values,
  preserves point order, rejects self-intersecting children and recompiles the
  visible mesh.
- VLM typed `set_control_point` edits may target a taper node only with
  `parameter_name=plan_control_points`; polygon validity is checked after edit.
- VLM remains a critic/reranker and typed graph editor. It is not falsely
  described as the surface generator.
- Final selection treats `oblique_envelope` as its own family, with minimum 1
  and maximum 2. It is no longer mislabeled as `folded_section`.

## Evidence

Representation harness on the real localized project parcel:

- `docs/playwright/design-route-live-verify/maas-oblique-envelope-genotype-probe-v1.json`
- `docs/playwright/design-route-live-verify/maas-oblique-envelope-genotype-probe-v1.png`
- 20/20 representation probes; every card is
  `agent_oblique_envelope_mesh`, 9-21 surfaces, operator
  `polygon_ring_loft`.
- This harness deliberately explores only the new genotype. It is not a final
  mixed-language board and must not be presented as such.

Real live-PNU loop chain (`1168011800104170004`):

1. v95: 18/20 and zero oblique candidates. This exposed invalid LLM control
   fields and led to strict author validation.
2. v96: 18/20 with one real oblique candidate. Full author -> compile ->
   capacity -> VLM -> selector connectivity was proven.
3. v97: 20/20, technical pass, one oblique candidate, but visual status still
   failed because stepped capacity was 2/3.
4. v98: 20/20, technical pass, mean VLM 0.7324, 20 measured geometric
   languages, zero near/morphology/silhouette repeat pairs, and exactly one
   oblique candidate. Visual status still honestly fails because stepped
   capacity remains 2/3.

Latest mixed board:

- `docs/playwright/design-route-live-verify/maas-neighborhood-vlm-a2a-v98-stepped-replenish-accepted-only.png`
- group counts: folded 4, continuous 3, oblique 1, bridge 3, cluster 2,
  carved 5, stepped 2.
- selected oblique card: one volume, 15 surfaces, five authored plan points,
  normalized FAR utilization 1.0, capacity fit 1.0, VLM 0.69, language geometry
  pass.

Do not call v98 a full visual pass or competition-grade. It is proof that the
new oblique language can coexist in the actual full loop. The overall board is
still visually conservative and misses one stepped-capacity minimum.

## Verification performed

- Focused oblique/section/search/VLM graph-edit tests: 4 passed.
- Direct compiler checks: one volume, correct 9-21/12/15/18 surface ranges,
  `polygon_ring_loft` operator preserved through site-frame rotation.
- The entire large `test_maas_program_massing.py` suite exceeded a 180-second
  command timeout; do not record it as a pass. Focused affected contracts pass.
- PNGs were opened and visually inspected, not accepted from counters alone.

## Next work

The oblique capability is connected. The immediate blocker is now the third
clean stepped-capacity survivor, not more polygon templates. Diagnose why the
fresh authored stepped graph is not distinct/admitted, keep the stepped hard
minimum, and avoid padding with a weak cake-tier box. After visual acceptance,
run the deterministic law/FAR/parking projection and measure geometry
retention; it remains `not_run` for these offline boards.

