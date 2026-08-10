# Failure ledger

- C24: exact legal fit passed; capacity utilization `0.45632722`, rejected.
- C25: exact whole-solid affine fit infeasible, rejected.
- C27: exact whole-solid affine fit infeasible, rejected.
- C28: compiler-only preflight was mistakenly treated as sufficient; canonical
  found whole-solid affine fit infeasible. This is the harness gap that must not recur.
- C29: same compiler-only preflight gap and affine-fit failure.
- C30-02: production fit passed, utilization `0.571148`, correctly rejected
  before freeze.
- C30-03, C31-01, C31-02, C32: production selector returned null; rejected
  before freeze/canonical.
- C33: exact fit rows existed, but utilization was `0.34996` and `0.36866`;
  rejected before freeze/canonical.
- C34: v31 `cube x 1/1 x interlock` compiled cleanly, but the production
  selector returned null; interlocking expansion could not fit the live field.
- C35: near-full cube source (`0.9938` normalized volume) plus `1/1 pinch`
  compiled cleanly, but constant-height top width forced global scaling below
  the selector's `.35` aggregate threshold; selector returned null.
- C36: continuous source compiled, but `1/16 short-axis shear` produced
  `empty_operator_result`. Its draft also exposed invalid taper keys
  `start/end`; the parser now rejects unknown parameters instead of allowing
  compiler defaults to hide them.
- C37: corrected taper keys compiled and BOOK compiled, but the production
  selector returned null. Its `notch.ratio=.022` also exposed missing value
  validation; the shared LLM parser now enforces numeric bounds, enums, and
  vector lengths before any candidate reaches the compiler.
- C38: harness-invalid, not a portfolio candidate. A one-candidate sequential
  run incorrectly built its BOOK offer with `count=8` (32 paths); the selected
  path was absent from the real `count=1` offer (16 paths). Never report a
  short-gate result unless author target count, offer count argument, parser
  expected count, and batch count describe the same request.
- C39: the corrected one-candidate offer contract passed, but the LLM selected
  `1/16 long-axis compress`; selector returned null. Probing the same frozen
  LLM source against all 16 actually offered paths took 36.044 s: only `1/1
  short-axis bend+stack` fit, at utilization `0.37148099`; no path reached
  `0.70`. This proves path names alone are insufficient guidance and the whole
  frozen source/path neighborhood must be measured before another source turn.
- C40: the LLM repeated a three-level setback source despite the stepped-family
  negative memory. All 16 offered BOOK paths compiled, but none exact-fit;
  batch runtime was 57.861 s. The shared parser now accepts a measured
  `author_forbidden_body_rule_families` retry contract and rejects `step`
  operators before expensive path probing when that family is overrepresented.
- C41: dynamic source bans passed and produced a new wedge/difference topology,
  but the wedge removed only about 2.8% of source volume. All 16 BOOK paths
  compiled, none exact-fit, in 36.864 s. Do not stack a speculative source body
  rule with another BOOK body rule when the BOOK graph should carry the primary
  architecture; probe a minimal authored base-form/Matrix/access carrier next.
- C42: one compact LLM-authored `cube -> Matrix4 -> notch` source and all 16
  offered BOOK paths compiled, but the selector-only probe reported `0/16`.
  Root-cause tracing proved this was not a valid terminal result: selector null
  already routes to the floorwise materializer, whose two global-fit calls had
  disabled its generic legal-CSG branch. The existing CSG boolean also bundled
  a coded pose/aspect search, so it must not simply be switched on. Fixed-pose
  CSG was separated from pose reflow. A diagnostic using the old pre-fitted
  source reached `332.3216488796 m2` proxy GFA (`0.99999894`), but that result
  was invalid as final evidence because the preliminary host fit masked visual
  distortion. After replacing it with normalized identity export, the real
  hard gate correctly rejected C42: continuous legal CSG changed phenotype
  `oblique -> prismatic`, silhouette distance `0.686358 > 0.4`. C42 remains
  rejected and unfrozen; feed this typed identity failure to the next LLM turn.
- C43: the next OAuth LLM source was genuinely new
  (`elliptical -> Matrix4 -> carve_void`) and selected the offered `1/1
  long-axis extrude` path. Parser and source compiler passed, but the selected
  BOOK program initially failed the normalized source-export boundary. Root
  cause was authority mixing: normalized transport incorrectly applied a
  site-containment `covers()` predicate to reconstructed proxy sections. The
  section exceeded its internal convex-hull carrier by only `0.00008461 m2`
  with zero boundary distance. Removing site containment from normalized
  transport (while retaining positive/valid polygon checks) fixed that common
  exporter path without a tolerance or morphology recipe. The same C43 then
  reached production floor fit but floor index 2 had `achieved_area_m2=0`
  against target `67.49`; its authored fixed pose did not overlap the shifted
  upper legal field. C43 is rejected unchanged. Feed the empty upper-band
  overlap to the next LLM Matrix4 authoring turn; deterministic code must not
  invent a compensating pose.
- C44: the LLM authored one vertically sheared compact carrier
  (`box -> Matrix4 -> cut_corner -> WEST notch`) and selected `3/8 vertical
  extrude`. Source compile passed. The selected path reached legal CSG but
  failed identity (`stepped -> prismatic`, distance `0.696166`). Full
  production probing of all 16 offered paths took `91.603 s` and produced
  `0/16` passes: identity distances were `0.626507..0.691633`, with the rest
  failing floor fit, authored-mesh completeness, or source compile. Direct
  materializer evidence for the selected path measured floor areas
  `[7.565151, 102.930961, 74.989012, 11.705628]` against targets
  `[92.638, 92.638, 67.49, 46.324]`, aggregate feasible utilization
  `0.593373`. The middle legal plates saturated while both endpoints emptied;
  author the next continuous section profile from this measured vector rather
  than weakening identity or capacity gates.

- C45: the OAuth LLM authored a new `box -> Matrix4 -> pinch -> WEST notch`
  topology and selected the exact offered `1/1 short_axis shift` BOOK path.
  A coordinate-unit defect in authoritative-surface comparison normalized
  already-normalized surface Z by the plan major axis, producing false
  silhouette distances around `0.69`. Normalizing Z by its own span made the
  unit-invariance regression pass. With unchanged legal/capacity thresholds,
  C45 materialized at `299.181101 m2` proxy GFA and `0.900275` feasible
  utilization. Its first isolated probe omitted the production
  capacity-alternative binding and therefore stopped at `semantic_carrier`;
  supplying the same nonempty binding fields used by the production caller
  completed materialization. However, the rendered MASS is visibly stepped
  because the selected BOOK operator itself is `shift`; it is diagnostic
  evidence, not yet a frozen/canonical portfolio member. The next LLM turn
  must select a non-stepped offered BOOK language rather than changing the
  fixed-pose legal fitter or relaxing identity thresholds.
- C46: the next OAuth LLM response avoided stepped BOOK operators and authored
  `box -> Matrix4 -> bend -> WEST notch` with the exact offered `1/1 vertical
  pinch` path. Source compile was clean, but the 31.057 s production
  materializer rejected it at `authored_visual_authority` with
  `profiled_legal_clip_invalid_authored_manifold`. C46 is unfrozen. Feed that
  typed manifold failure to a fresh, simpler continuous topology/path; do not
  repair the rejected AST by hand.
- C47: a fresh OAuth response simplified the source to `box -> Matrix4 -> WEST
  carve_void` and selected exact offered `3/8 vertical lift`. Source compile
  was watertight/manifold/one-component, but production rejected
  `pyramidal -> prismatic` authored identity collapse at silhouette distance
  `0.691655 > 0.4`. The small BOOK fraction could not survive the required
  legal/capacity projection without replacement-scale distortion. Prefer a
  newly offered `1/1` non-stepped path next; do not lower the identity gate.
- C48: the LLM chose the only robust non-banned `1/1` offer in its slice,
  `long_axis inscribe`, with a clean `box -> Matrix4 -> WEST notch` source.
  It exposed a deterministic fitter bug: fixed-pose legal CSG assumed
  intersection area grew monotonically with uniform scale. For concave/voided
  bodies the legal host can enter the authored void, so the loop overwrote a
  better lower sample with the last shrinking sample. Before the fix the
  global scales reached `[27.054035, 17.48869]`, clipped `161..182 m2` per
  floor, retained only `9.5474 m2`, and collapsed `winged -> prismatic` at
  distance `0.700399`. The fitter now retains the maximum sampled lower; a
  ring/host regression proves the non-monotonic case. C48 then preserved
  `winged -> winged` and improved distance to `0.547727`, but achieved only
  `[35.2819, 32.9569, 26.0120, 17.9353] m2`, so it still fails identity and
  capacity and remains unfrozen.
- C49: its exact offer slice contained no eligible non-banned `1/1` path, so
  the LLM selected `3/8 short_axis merge` with `box -> Matrix4 -> WEST notch`.
  It genuinely materialized at `299.091713 m2`, utilization `0.900006`, and
  preserved authored identity at distance `0.24445`; however both authored
  and projected phenotypes are `stepped`, and the inspected PNG confirms the
  same stair mass. It remains diagnostic/unfrozen. Do not waste another LLM
  call on a window without a `1/1` non-stepped option: scan graph windows
  first, then author once against an eligible exact offer set.
- C50: graph-window scheduling scanned offsets `540,560,580,600` and skipped
  them because the exact request had no eligible non-banned `1/1` path. Offset
  `620` supplied `1/1 long_axis rotate`; the OAuth LLM authored `box ->
  Matrix4 -> cut_corner -> WEST notch`. It materialized at `292.174303 m2`,
  utilization `0.87919`, with identity distance `0.240270` and phenotype
  `winged -> oblique`. Its certificate is
  `floorwise_profiled_continuous_envelope_clip`, `visible_step_fallback=false`,
  and only two horizontal surface levels, so it is not the old floor-plate
  staircase fallback. Nevertheless the inspected board remains visually close
  to the setback family; retain it as a strong diagnostic but require later
  plan/section families to be materially different before a 20-item board.
- C51: scheduled offset `660` supplied exact `1/1 vertical split+join` and the
  OAuth LLM authored a clean `box -> Matrix4 -> WEST notch`. The certified
  projected surface visibly retained a central split; identity distance was
  `0.230079` and achieved floor areas were
  `[95.083, 95.083, 71.719, 50.084]`. It correctly failed semantic authority:
  `required_carrier_projection_empty:public_spatial_gesture`. The pre-LLM BOOK
  source's `neighborhood_entry_canopy` had exactly `0.0 m2` overlap with the
  source footprint, so the public gesture was detached. C51 remains unfrozen.
  Future graph scheduling must source-compile offered BOOK paths and require
  public-role/primary-footprint overlap before paying for another LLM call.
- C52: BOOK semantic preflight selected exact `1/1 long_axis lift+carve` only
  after proving public platform overlap `12.466877 m2`, entry canopy overlap
  `10.076534 m2`, connected primary relation, and no explicit stepped proxy
  label. Production materialization passed GFA `299.446510 m2`, utilization
  `0.901073`, identity distance `0.203131`, and all semantic relations. The
  actual authored/projected phenotype was nevertheless `stepped` with six
  horizontal levels; inspected PNG confirms it. Proxy metadata is therefore
  only preflight evidence, never final visual classification. C52 remains
  unfrozen and excluded from the diverse portfolio.
- C53-B01: the workflow switched to one 20-program OAuth batch. Deterministic
  preflight produced 20 exact eligible BOOK path IDs across eight favored
  operation families with a per-family cap of three. The single provider call
  started and terminated immediately because the Codex OAuth account hit its
  usage limit; it was not a prompt/schema/context failure. Provider request
  count `1`, response absent, parsed/compiled `0/0`. The provider instructed
  retry at `2026-08-09 13:00 KST`. Do not split/retry or manufacture algorithmic
  replacements while OAuth authorization is unavailable and LLM authorship is
  mandatory. Evidence SHA-256:
  `dddc3a3b258fc725678172f529c2ed9f71526ecad51c9577d8ef265362606ecb`.

Never tune a frozen rejected AST. Author a fresh topology/path using only typed
measured feedback.
